import json
import os

from Profile import Profile


class Profiles:
    """
    In this class the different soldering profiles are managed.

    Methods
    -------
    profile_list: list
        A list of all selectable profiles.
    save_profiles()
        Saves the current profile list in "storage/profiles.json".
    add_profile(profile_id, name, data)
        Adds a new soldering profile to the profile list.
        A profile must consist an ID, a name and the data points.
    delete_profile(profile_id)
        Deletes a specific profile from the profile list.
    selected_profile()
        Get the selected profile / set the profile with the passed ID as the current profile.
    """

    def __init__(self):
        self._profile_list = []
        self._profiles_loaded = False

        self.selected_profile = self.profile_list[0].id

    @property
    def profile_list(self):
        """
        If the profiles are not already loaded from the JSON file, they will be loaded from "storage/profiles.json"
        and returned as profile object list. Otherwise, the list stored in _profiles_list is returned to avoid having
        to read from the JSON file each time.

        Returns
        -------
        list
           A list containing all soldering profiles.
        """
        if not self._profiles_loaded:
            if os.path.exists(os.path.join('reflow_oven', 'storage')):
                base_dir = os.path.join('reflow_oven', 'storage')
            else:
                base_dir = 'storage'

            input_file = open(os.path.join(base_dir, 'profiles.json'))
            profiles = json.load(input_file)

            for profile in profiles:
                self._profile_list.append(Profile(profile['id'], profile['name'], profile['data']))

            self._profiles_loaded = True
            return self._profile_list
        else:
            return self._profile_list

    def save_profiles(self):
        """
        Saves the current profile list in "storage/profiles.json".
        """
        if os.path.exists(os.path.join('reflow_oven', 'storage')):
            base_dir = os.path.join('reflow_oven', 'storage')
        else:
            base_dir = 'storage'

        profiles = []
        for profile in self.profile_list:
            profiles.append({'id': profile.id, 'name': profile.name, 'data': profile.data})
        with open(os.path.join(base_dir, 'profiles.json'), 'w') as output_file:
            json.dump(profiles, output_file)

    def add_profile(self, profile_id, name, data):
        """
        Adds a new soldering profile to the profile list.
        A profile consists of an ID, a name and the data points.

        Parameters
        ----------
        profile_id: str
            The unique ID of the profile.
        name: str
            The name of the profile.
        data: list
            The data points (time and temperature) of the profile.
        """
        # check if the id already exits
        result = next((profile for profile in self.profile_list if profile.id == profile_id), None)

        if result is None:
            profile = Profile(profile_id, name, data)
            profile_list = self.profile_list
            profile_list.append(profile)

            self._profile_list = profile_list
            self.save_profiles()

    def update_profile(self, profile_id, name, data):
        profile_list = self.profile_list

        found_profiles = [i for i in range(len(profile_list)) if profile_list[i].id == profile_id]

        if len(found_profiles) > 0:
            index = found_profiles[0]
            profile_list[index].name = name
            profile_list[index].data = data
            self._profile_list = profile_list
            self.save_profiles()

    def delete_profile(self, profile_id):
        """
        Deletes a specific profile from the profile list.

        Parameters
        ----------
        profile_id: str
            The ID of the profile to be deleted
        """
        index = None
        # check if the id already exits
        for i in range(len(self.profile_list)):
            if self.profile_list[i].id == profile_id:
                index = i
        if index is not None:
            self.profile_list.pop(index)
            self.save_profiles()

    @property
    def selected_profile(self):
        """
        Returns
        -------
        dict
            The currently selected profile.
        """
        return next((profile for profile in self.profile_list if profile.selected is True), None)

    @selected_profile.setter
    def selected_profile(self, profile_id):
        if self.selected_profile:
            self.selected_profile.selected = False
        new_selected_profile = next((profile for profile in self.profile_list if profile.id == profile_id), None)
        if new_selected_profile:
            new_selected_profile.selected = True
